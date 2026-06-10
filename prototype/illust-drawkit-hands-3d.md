# DrawKit Hands Illustrations (illust)

**Tag:** illust-drawkit-hands-3d  ·  **Category:** 3D  ·  **Role affinity:** spot-illustration

anatomically simplified but realistically lit hand renders.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/illustration-library.md`](../docs/research/illustration-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
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
```

## When NOT to use

cartoon contexts, brutalism, dense data UI

## Pairs with (prototype slugs)

- `recipe-restrained-ai-marketing`
- `style-liquid-glass`
- `style-sf-pro-ios`
- `recipe-ios-system`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 156–188 of `docs/research/illustration-library.md`. Full index: `docs/research/illustration-library.index.json`._
