# Datamosh (codec interpolation failure) (material)

**Tag:** material-datamosh-compression-smear  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: datamosh-compression-smear
  name: Datamosh (codec interpolation failure)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes — frame motion stretches old pixels along predicted vectors
    age: ageless (or feels 2008-Tumblr era)
  implementationStrategies:
    css: |
      /* approximation only — true datamosh needs WebGL */
      filter: blur(0.5px) saturate(1.2);
      mix-blend-mode: screen;
    webgl: |
      sample previous frame, displace UVs by motion vectors derived from current
      frame's flow field; never refresh the I-frame. Shadertoy "datamosh" examples
      from beesandbombs and dwitter are the references. Best driven by an
      input video (mp4) and shader stage.
    raster: pre-rendered datamosh video texture under content (looped mp4 or webm)
  reactiveBehaviors:
    light: none — datamosh smears existing pixels
    highlight: pointer can seed the motion-vector field for interactive smear
    depth: stuck-frame "pause" reads as compressed time
    parallax: motion compounds with scroll position (each scroll-tick adds a smear)
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-acid-design, aesthetic-y2k-futurism, aesthetic-dreamcore, aesthetic-weirdcore]
  killsTheIllusion:
    - datamosh over still imagery (it needs motion to smear)
    - clean cuts between datamoshed clips (real datamosh is continuous)
    - excessive opacity (datamosh reads as material, not as filter)
  examples:
    - Kanye West "Welcome to Heartbreak" music video
    - Takeshi Murata datamosh fine-art
    - Sapeur album covers
  references:
    - https://www.shadertoy.com/results?query=datamosh
```

## Common implementation mistakes (avoid these)

- datamosh over still imagery (it needs motion to smear)
- clean cuts between datamoshed clips (real datamosh is continuous)
- excessive opacity (datamosh reads as material, not as filter)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cyberpunk`
- `aesthetic-acid-design`
- `aesthetic-y2k-futurism`
- `aesthetic-dreamcore`
- `aesthetic-weirdcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 965–1003 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._
