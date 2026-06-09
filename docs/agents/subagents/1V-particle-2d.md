# Subagent 1.V.particle-2d — Asset drawer (medium: canvas 2D particle loop)

You own **ONE asset** of medium `particle-2d` — an ambient particle loop rendered with Canvas 2D (no WebGL). Drift, snow, sparks, dust, gentle field motion. **Pathway B**: you write the canvas JS directly.

Why Canvas 2D and not WebGL? Lower setup cost, broader compatibility, easier to debug, sufficient for ≤200 particles. If the brief demands thousands of particles or instanced rendering, the medium should be `particle-gl`, not `particle-2d` — return `error: "density requires particle-gl medium"`.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","canvas-skill"]
nodeIds: { prompt, skill, asset }
```

Slot is typically `<canvas id="bg-…" data-effect="…">` or `<canvas data-particles="…">`. The runtime mount loop binds a 2D context to the slot and evals your code with `ctx` and `canvas` exposed; you register a frame callback via `__animate(t => …)` (same convention as the 3D drawer).

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<1-sentence design intent — what the field represents>",
  "skillCode": "<full canvas-2d code as a single string>",
  "params": {
    "outputPath": "<slot.outputPath e.g. assets/canvas/bg-drift.js>",
    "density": "<count, e.g. 60>",
    "performance": "background" | "hero"
  },
  "slotEditDiff": "<diff or null>"
}
```

## Recipe

### 1. Read slot + genre + `data-motion` modifier

The motion modifier on the slot is the brief. Read it:

```html
<canvas data-effect="drift" data-motion="particles · slow drift · 40 dots warm white">
```

- `data-effect` is the family (`drift`, `snow`, `sparks`, `dust`, `field`)
- `data-motion` is the design intent — particle count hint, speed adjective, palette anchor

Genre filter applies: only Marketing / Bento / Editorial-divider / Marketing-consumer can carry this medium.

### 2. Pick a particle archetype

| Archetype | Family | Geometry | Motion |
|---|---|---|---|
| Drift | `drift` | Soft circles, low alpha | Slow vertical or diagonal, with mild noise jitter |
| Snow | `snow` | Filled white circles, varying size | Vertical with sinusoidal sway, wrap at bottom |
| Sparks | `sparks` | Tiny bright dots with motion-blur tail | Outward burst from a focal point, decay alpha |
| Dust | `dust` | Wide soft glow circles | Brownian, very slow, low alpha |
| Field | `field` | Short line segments | Vector-field flow following `noise(x, y, t)` |

### 3. Code template

```js
// ctx and canvas are pre-bound by the host. __animate registers a frame fn.

const DPR = Math.min(window.devicePixelRatio || 1, 2);
function resize() {
  canvas.width  = canvas.clientWidth  * DPR;
  canvas.height = canvas.clientHeight * DPR;
}
resize();
addEventListener("resize", resize);

const COUNT = 60;
const particles = Array.from({ length: COUNT }, () => spawn());

function spawn(p = {}) {
  return {
    x:    p.x ?? Math.random() * canvas.width,
    y:    p.y ?? Math.random() * canvas.height,
    vx:   (Math.random() - 0.5) * 0.3,
    vy:   0.2 + Math.random() * 0.4,
    r:    0.6 + Math.random() * 1.6,
    a:    0.15 + Math.random() * 0.35
  };
}

const COL = "rgba(255, 248, 235,";    // anchor to --surface or --text

__animate((t) => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.y > canvas.height + 4) Object.assign(p, spawn({ y: -4 }));

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r * DPR, 0, Math.PI * 2);
    ctx.fillStyle = COL + p.a.toFixed(2) + ")";
    ctx.fill();
  }
});
```

Adapt per archetype:

- **Sparks** → outward velocity from focal point, decay `p.a` over lifetime, respawn on death.
- **Field** → replace per-particle velocity with a noise-sampled vector each frame: `const angle = noise(p.x*0.01, p.y*0.01, t*0.0002) * Math.PI * 2`.
- **Dust** → tiny Brownian increments `p.vx += (Math.random()-0.5)*0.02`, clamp velocity.

### 4. Performance budget

| Performance | Particle count | Per-particle ops |
|---|---|---|
| `background` (default) | ≤80 | One `fillStyle` set + one `arc` + position math. No `shadowBlur`. |
| `hero` | ≤200 | May use `globalCompositeOperation = "lighter"` for glow, may use one `shadowBlur` |

If `background` and the brief asks for glow, fake it with multiple offset draws of the same particle at decreasing alpha — cheaper than `shadowBlur`.

### 5. Palette — anchor to tokens

Hardcode the rgba string by reading `:root`:

```js
// --surface: oklch(99% 0.002 80)  ≈ rgb(255, 252, 245)
const COL = "rgba(255, 252, 245,";
```

Or read `getComputedStyle(canvas).getPropertyValue("--surface")` at mount time — that's the cleaner version. Use the computed approach if the prototype has a brand toggle (`data-mode="lxp"` vs `"pxp"`).

### 6. DPR + resize handling — mandatory

Without DPR scaling, particles look blurry on retina screens. Without a resize handler, particles cluster after window resize. Both are non-negotiable — see code template.

### 7. Slot diff

If the slot isn't declared yet:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"hero-bg\">",
  "replace": "<canvas class=\"hero-bg\" data-particles=\"<assetId>\"></canvas>"
}
```

## Self-audit

- [ ] Genre allows particle motion. Otherwise returned `error`.
- [ ] Particle count matches `density` param and respects `performance` budget.
- [ ] DPR scaling present.
- [ ] Resize handler present.
- [ ] Palette anchored to `:root` tokens (hardcoded or computed at mount).
- [ ] No `shadowBlur` unless `performance: hero`.
- [ ] No `requestAnimationFrame` inside scene code (use `__animate(fn)`).
- [ ] Respawn logic prevents off-canvas particles from accumulating.
- [ ] Code is self-contained — no external imports, no library references.

## Don't

- Don't ship more than 80 particles in `background` performance — even modern phones throttle this.
- Don't use `setInterval` for the frame loop. `__animate(fn)` is the contract.
- Don't draw with `shadowBlur` per particle in `background` — pixel-fill cost is 10× a flat `arc`.
- Don't reference any color string that isn't anchored to the token system. Random colors break theme switching.
- Don't combine multiple archetypes in one canvas. If the brief wants "snow with sparks", that's two separate slots.
