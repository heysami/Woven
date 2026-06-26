# Woven -> Figma scene contract

The editor's DOM walker (`editor/figma-bridge.js`, `window.WovenFigma.domToScene`)
emits this JSON; the plugin sandbox (`code.js`) rebuilds it as Figma nodes. Keep
both sides in sync when extending the schema.

```jsonc
{
  "version": 1,
  "name": "Landing page",     // names the top frame in Figma
  "width": 1280,
  "height": 3200,
  "imageBytes": 1234567,      // diagnostic: total inlined raster size
  "root": { /* node */ }
}
```

## node

```jsonc
{
  "type": "FRAME" | "TEXT" | "IMAGE",
  "name": "section.hero",
  "x": 0, "y": 0,            // position RELATIVE to the parent node
  "width": 1280, "height": 720,

  // optional, all node types
  "opacity": 0.9,            // omitted when 1
  "clipsContent": true,      // overflow:hidden
  "fills":   [ Paint, ... ], // paint order = CSS paint order (bg color, then image)
  "strokes": [ Paint ],      // SOLID only; CSS border
  "strokeWeight": 1,
  "cornerRadius": 8 | { "tl":8, "tr":8, "br":0, "bl":0 },
  "effects": [ Effect, ... ],// box-shadow

  // TEXT only
  "characters": "Get started",
  "fontSize": 16,
  "fontFamily": "Inter",
  "fontStyle": "SemiBold",   // mapped from font-weight + italic
  "letterSpacing": 0.2,      // px
  "lineHeight": 24 | "AUTO", // px or AUTO
  "textAlign": "LEFT" | "CENTER" | "RIGHT" | "JUSTIFIED",
  "textColor": Paint,        // SOLID
  "textDecoration": "NONE" | "UNDERLINE" | "STRIKETHROUGH",

  // IMAGE only (also <img>)
  "image": { "b64": "...", "mime": "image/jpeg" },

  // optional: when present the plugin builds a Figma AUTO-LAYOUT frame and
  // children flow by order (their x/y are ignored, except absolute ones).
  "layout": {
    "mode": "HORIZONTAL" | "VERTICAL",
    "gap": 12,                               // itemSpacing (main-axis)
    "crossGap": 0,                           // counterAxisSpacing when wrapping
    "padding": { "top":0, "right":0, "bottom":0, "left":0 },
    "primaryAlign": "MIN" | "CENTER" | "MAX" | "SPACE_BETWEEN",  // justify-content
    "counterAlign": "MIN" | "CENTER" | "MAX" | "BASELINE",       // align-items
    "wrap": false
  },
  "absolute": true,          // CSS position:absolute/fixed; under an auto-layout
                             // parent it is taken out of flow and kept at x/y

  "children": [ node, ... ]
}
```

## Paint

```jsonc
{ "type": "SOLID", "color": { "r":0..1, "g":0..1, "b":0..1 }, "opacity": 0..1 }
{ "type": "GRADIENT_LINEAR", "angle": 180, "stops": [ { "position":0..1, "color": {r,g,b,a} } ] }
{ "type": "IMAGE", "scaleMode": "FILL", "image": { "b64", "mime" } }
```

## Effect

```jsonc
{ "type": "DROP_SHADOW" | "INNER_SHADOW",
  "offsetX": 0, "offsetY": 2, "radius": 8, "spread": 0,
  "color": { "r":0..1, "g":0..1, "b":0..1, "a":0..1 } }
```

## Layout

CSS flexbox maps to Figma auto-layout precisely (direction, gap, padding,
justify-content, align-items, flex-wrap, and `order`). Plain block containers
go through a guarded heuristic: a clean, evenly-spaced, non-overlapping stack of
children becomes a VERTICAL (or HORIZONTAL) auto-layout; anything with
overlapping or irregularly-spaced children stays absolute (`layout` omitted), so
the converter never invents a layout that mangles the design. CSS grid stays
absolute for now (no Figma equivalent yet).

## Limitations (intentional)

- Children inside an auto-layout keep their measured size (FIXED), so the result
  matches the render while staying re-flowable; per-child margins are not
  modelled (auto-layout uses one gap), and `space-around`/`space-evenly` collapse
  to `SPACE_BETWEEN`.
- CSS transforms (rotation/scale) are baked into x/y/size by
  `getBoundingClientRect`, so a rotated element lands un-rotated at its rendered
  box.
- `<canvas>`, inline `<svg>`, and `<video>` are walked as plain frames (their
  box decoration only). Rasterizing them via the already-loaded `html2canvas-pro`
  is the planned upgrade.
- One box-shadow / one linear-gradient layer is parsed (the first).
- Cross-origin images that block CORS fall back to a neutral gray fill.
