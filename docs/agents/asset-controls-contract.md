# Asset controls contract — auto-exposed knobs for generated assets

When you produce an HTML asset (shader / motion / 3D / any interactive HTML), expose
the handful of variables a user would naturally want to tweak so the editor can
render them as a floating **Controls** panel on the selected asset node — color,
speed, timing, easing, width, scale, count, etc. The user adjusts them live; no
re-prompt, no regeneration.

## How it works

Asset iframes are same-origin in the editor. The editor reads a global registry you
install, `window.__wovenControls`, and calls `.set(key, value)` on every input. A
shared shim provides the registry; you only declare the knobs.

### 1. Include the shim (once, in `<head>`, BEFORE your own register calls)

```html
<script src="/editor/tools/_shared/asset-controls.js"></script>
```

This path is served by the daemon in the editor. In a standalone/export context it
404s harmlessly — that is why every register call is guarded (see below).

### 2. Register each knob with a live setter

`apply(value)` is YOUR function that pushes the new value into the running asset
(write a uniform, retime a timeline, set a scene handle, set a CSS var). Register
AFTER the variable/uniform the setter touches exists.

```html
<script>
  // Guarded so a standalone export (no shim) never throws.
  var C = window.__wovenControls;
  if (C) {
    C.register({ key: "speed", label: "Speed", type: "range",
      min: 0, max: 4, step: 0.01, default: 1, group: "Motion",
      apply: function (v) { SPEED = v; } });            // read SPEED in your loop
    C.register({ key: "tint", label: "Tint", type: "color", default: "#7c5cff",
      group: "Color", apply: function (v) { U_TINT = hexToRgb(v); } });
  }
</script>
```

### Control types

| type     | widget        | value          | notes |
|----------|---------------|----------------|-------|
| `range`  | slider        | number         | needs `min`, `max`, `step` |
| `number` | slider        | number         | alias of range |
| `color`  | colour picker | `#rrggbb`      | convert to your own format in `apply` |
| `select` | dropdown      | string         | needs `options: [...]` |
| `easing` | dropdown      | CSS easing str | preset easing list |
| `toggle` | checkbox      | boolean        | |

`group` buckets knobs into labelled sections (`Color`, `Motion`, `Timing`,
`Geometry`, …). `default` is applied immediately on register so the first frame
matches the panel.

## What to expose (aim for 3–8 knobs, the ones that matter)

- **Shader**: primary tint/accent colour(s), animation speed, scale/zoom, intensity.
- **Motion**: total duration, easing, start delay; expose a colour if the piece has a brand fill. `apply` should retime the paused GSAP timeline (e.g. `TL.duration(v)` / `TL.timeScale(base/v)`) and re-seek.
- **3D**: rotation/orbit speed, a key material colour, camera distance/zoom, light intensity. Drive them through the handles you already expose on `window.__scene3d`.

Keep it to the knobs a designer would actually reach for. Do not expose every
internal variable; that makes the panel noise.

## Fallback (you usually don't need to do anything)

If you skip the shim entirely but drive your asset from CSS custom properties on
`:root` with common names (`--speed`, `--accent`, `--duration`, `--ease`,
`--width-start`, `--scale`, …), the editor auto-detects those and shows a best-effort
panel. Explicit `register()` with labelled controls + bespoke setters is always
better — use the shim when you can; the CSS-var fallback is the safety net for
assets that predate this contract.
